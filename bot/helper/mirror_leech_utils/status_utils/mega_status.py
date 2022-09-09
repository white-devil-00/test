from time import time
from asyncio import sleep
from bot import EDIT_SLEEP_SECS, status_dict, status_dict_lock
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from os import path as ospath
from bot.helper.ext_utils.human_format import human_readable_bytes
from bot.helper.ext_utils.message_utils import editMarkup, editMessage, sendMessage
from bot.helper.mirror_leech_utils.status_utils.status_utils import get_bottom_status


def get_download_info(mega_client, gid):
    dl_info = mega_client.getDownloadInfo(gid) 
    return dl_info

class MegaDownloadStatus:
     def __init__(self, gid, message, obj):
        self.__gid = gid
        self.__message= message
        self.id = self.__message.id
        self._status_msg= ""
        self._obj= obj
        self._client= self._obj.mega_client
        self._dl_info= get_download_info(self._client, gid)

     def get_status_msg(self):
          return self._status_msg     

     async def create_status(self):
        async with status_dict_lock:  
            status_dict[self.id] = self
        status_msg = await self.create_update_message()    
        rmsg= await sendMessage(status_msg, self.__message)
        sleeps= False
        start = time()
        while True:
               self._dl_info = get_download_info(self._client, self.__gid)
               if self._dl_info is not None:
                    sleeps = True
                    self._status_msg = await self.create_update_message()
                    if time() - start > EDIT_SLEEP_SECS:
                         data = "cancel_megadl_{}".format(self.gid())
                         await editMarkup(self._status_msg, rmsg, reply_markup=(InlineKeyboardMarkup([
                                             [InlineKeyboardButton('Cancel', callback_data=data.encode("UTF-8"))]
                                             ]))) 
                         if sleeps:
                              if self._obj.is_cancelled:
                                   await editMessage("Download Cancelled", rmsg)
                                   async with status_dict_lock:
                                        del status_dict[self.id]
                                   return False, rmsg, None
                              if self._obj.is_completed:
                                   path = ospath.join(self._obj.dl_add_info["dir"], self._dl_info["name"])
                                   async with status_dict_lock:
                                        del status_dict[self.id]
                                   return True, rmsg, path
                              sleeps = False
                              await sleep(1)

     async def create_update_message(self):
        download = self._dl_info
        msg =  "<b>Name:</b> {}\n".format(download["name"])
        msg += "<b>Status:</b> Downloading...\n"
        msg += "{}\n".format(self.__get_progress_bar(download["completed_length"], download["total_length"]))
        msg += "<b>P:</b> {}%\n".format(round((download["completed_length"]/download["total_length"])*100, 2))
        msg += "<b>Downloaded:</b> {} of {}\n".format(human_readable_bytes(download["completed_length"]),
            human_readable_bytes(download["total_length"]))
        msg += "<b>Speed:</b> {}".format(human_readable_bytes(download["speed"])) + "|" + "<b>ETA:</b> <b>N/A</b>\n"
        msg += get_bottom_status()
        return msg

     def __get_progress_bar(self, completed_length, total_length):
          completed = completed_length / 8
          total = total_length / 8
          p = 0 if total == 0 else round(completed * 100 / total)
          p = min(max(p, 0), 100)
          cFull = p // 8
          p_str = '■' * cFull
          p_str += '□' * (12 - cFull)
          p_str = f"[{p_str}]"
          return p_str
     
     def gid(self):
        return self.__gid

     async def cancel_download(self):
        self._obj.mega_client.cancelDl(self.gid())